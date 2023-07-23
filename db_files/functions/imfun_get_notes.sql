drop function if exists imfun_get_notes;

create or replace function imfun_get_notes(
    _query varchar,
    _page integer,
    _page_size integer,
    _name varchar,
    _tags varchar[],
    _favorites boolean
) returns table (
    id bigint,
    title varchar,
    content text,
    favorite boolean,
    "user" jsonb,
    tags jsonb,
    likes bigint
)
language plpgsql
as $$

declare
    _offset integer := (_page - 1) * _page_size;

begin
    return query
    select n.id, n.title, n."content", n.favorite,
        jsonb_build_object(
            'id', u.id ,
            'name', u."name"
        ) "user",
        jsonb_agg(
            distinct
            jsonb_build_object(
                'id', t.id,
                'name', t."name"
            ) 
        ) tags,
        count(nl.id) likes
    from notes n 
    join users u on u.id = n.user_id 
    left join notes_tags nt on n.id = nt.note_id  
    left join tags t on nt.tag_id = t.id
    left join notes_likes nl on nl.note_id = n.id 
    where
        n.active = true
        and case
            when _query is not null then
                n.title ilike '%' || _query || '%'
            else
                true
        end
        and case
            when _name is not null then
                n.title ilike '%' || _name || '%'
            else
                true
        end
        and case
            when _tags is not null then
                t.name = any(_tags)
            else
                true
        end
        and case
            when _favorites is not null then
                n.favorite = _favorites
            else
                true
        end
    group by n.id, u.id
    order by n.updated_at desc
    limit _page_size
    offset _offset;

end;    
$$;