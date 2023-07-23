drop function if exists imfun_update_user;

create or replace function imfun_update_user(
    _id uuid,
    _name varchar,
    _email varchar,
    _group_id bigint
)
returns table(
    id uuid,
    name varchar,
    email varchar,
    updated_at timestamptz,
    "group" jsonb
)
language plpgsql
as $$

begin
    update users
    set
        name = coalesce(_name, name),
        email = coalesce(_email, email),
        group_id = coalesce(_group_id, group_id)
    where
        id = _id;

    return query
        select * from imfun_get_user(_id::uuid);

end;
$$;
