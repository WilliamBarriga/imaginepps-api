drop function if exists imfun_create_note;

create or replace function imfun_create_note(
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
    total_likes bigint,
    likes jsonb
)
language plpgsql
as $$

declare
    _note_id bigint;

begin
    insert into notes (title, content, user_id, favorite)
    values (_title, _content, _user_id, _favorite)
    returning notes.id into _note_id;

    insert into notes_tags (note_id, tag_id)
    select _note_id, tags.id
    from tags
    where tags.name = any(_tags);

    return query
        select * from imfun_get_note(_note_id);
end;
$$;