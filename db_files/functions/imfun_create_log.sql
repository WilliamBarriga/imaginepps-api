drop function if exists imfun_create_log;

create or replace function imfun_create_log(
    _user_id uuid,
    _request jsonb,
    _response jsonb,
    _user_data jsonb,
    _url varchar
) returns void
language plpgsql
as $$
declare
    _route_id bigint;

begin

    select rp.id into _route_id
    from routes_permissions rp
    where rp.route ilike _url;

    insert into logs (
        user_id,
        request,
        response,
        user_data,
        route_permission_id
    ) values (
        _user_id,
        _request,
        _response,
        _user_data,
        _route_id
    );
end;
$$;