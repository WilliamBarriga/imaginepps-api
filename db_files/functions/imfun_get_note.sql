drop function if exists imfun_get_note;

create or replace function imfun_get_note(
    _id bigint
) returns table (
    id bigint,
    title varchar,
    content text,
    favorite boolean,
    "user" jsonb,
    tags jsonb,
    total_likes bigint,
    likes jsonb
)
language plpgsql
as $$

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
        count(nl.id) total_likes,
        jsonb_agg(
            DISTINCT
            jsonb_build_object(
                'id', u2.id,
                'name', u2."name"
            )
        ) likes
    from notes n
    join users u on u.id = n.user_id
    left join notes_tags nt on n.id = nt.note_id
    left join tags t on nt.tag_id = t.id
    left join notes_likes nl on nl.note_id = n.id
    left join users u2 on nl.user_id = u2.id
    where
        n.active = true
        and n.id = _id
    group by n.id, u.id;
end;
$$;
