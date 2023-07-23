drop function if exists imfun_get_user_data;

create or replace function imfun_get_user_data(
    _user_email varchar
) returns table (
    id uuid,
    name varchar,
    email varchar,
    active boolean,
    "group" jsonb,
    password varchar
)
language plpgsql
as $$

begin

return query
    select
        u.id,
        u.name,
        u.email,
        u.active,
        jsonb_build_object(
            'id', ug.id,
            'name', ug.name
        ) as group,
        u.password
    from users u
    join user_groups ug on ug.id = u.group_id
    where u.email = _user_email;

end;
$$;