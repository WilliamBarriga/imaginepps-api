drop function if exists imfun_create_log;

create or replace function imfun_create_log(
    _user_id int8,
    _request jsonb,
    _response jsonb,
    _user_data jsonb,
    _user_id int8
) returns void
language plpgsql
as $$
begin

    insert into logs (
        user_id,
        request,
        response,
        user_data,
        user_id
    ) values (
        _user_id,
        _request,
        _response,
        _user_data,
        _user_id
    );
end;
$$;