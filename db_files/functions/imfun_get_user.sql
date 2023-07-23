drop function if exists imfun_get_user;

create or replace function imfun_get_user(
    _id uuid
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

    return query
    select u.id, u.name, u.email, u.updated_at, jsonb_build_object(
        'id', ug.id,
        'name', ug.name
    ) as group
    from users u 
    join user_groups ug on u.group_id = ug.id
    where u.id = _id;

end;    
$$;