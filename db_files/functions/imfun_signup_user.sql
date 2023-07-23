drop function if exists imfun_signup_user;

create or replace function imfun_signup_user(
    _name varchar(255),
    _email varchar(255),
    _password varchar(255),
    _group_id bigint,
    out _user_id uuid
) 
language plpgsql
as $$

begin
    insert into users (name, email, password, group_id)
    values (_name, _email, _password, _group_id) 
    returning id into _user_id;
end;
$$;
