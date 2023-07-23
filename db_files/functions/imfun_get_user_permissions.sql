drop function if exists imfun_get_user_permissions;

create or replace function imfun_get_user_permissions(
    _user_group_id bigint,
    _url varchar,
    _method varchar,
    out _permission boolean
)
language plpgsql
as $$
declare
    _permission_id bigint;
    _exclude boolean;
begin
    select
        rp.id, rp."exclude" 
        into _permission_id, _exclude
    from
        routes_permissions rp
    where
        and rp.route = _url
        and rp.method = _method
        and rp.active = true
    
    if _exclude then
        _permission = false;
    else
        select
            count(*) > 0
            into _permission
        from
            user_groups_routes_permissions ugp
        where
            ugp.user_group_id = _user_group_id
            and ugp.permission_id = _permission_id
            and ugp.active = true
    end if;
end;
$$;
