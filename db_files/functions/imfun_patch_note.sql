
drop function if exists imfun_patch_note;

create or replace function imfun_patch_note(
    _id bigint,
    _title varchar,
    _content varchar,
    _tags varchar[],
    _favorite boolean,
    _user_id uuid
) returns table (
    id bigint,
    title varchar,
    content text,
    favorite boolean,
    "user" jsonb,
    tags jsonb,
    total_likes integer,
    likes jsonb
)
language plpgsql
as $$

declare
	_tag varchar;
    _tag_id bigint;

begin
    update notes
    set
        title = coalesce(_title, title),
        content = coalesce(_content, content),
        favorite = coalesce(_favorite, favorite)
    where notes.id = _id;

    if _tags is not null then
        update notes_tags
        set active = false
        where notes_tags.note_id = _id;

        for _tag in select * from unnest(_tags) loop
            select tags.id into _tag_id
            from tags
            where tags.name ilike _tag;

            if _tag_id is null then
                insert into tags (name)
                values (_tag);
            else
                update notes_tags
                set active = true
                where notes_tags.note_id = _id
                and notes_tags.tag_id = _tag_id;
            end if;

        end loop;

    end if;
end;
$$;