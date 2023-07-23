drop function if exists imfun_like_note;

create or replace function imfun_like_note(
    _note_id bigint,
    _user_id uuid
) returns void
language plpgsql
as $$

begin
    insert into notes_likes (note_id, user_id)
    values (_note_id, _user_id);
end;
$$;