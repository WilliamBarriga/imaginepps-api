drop function if exists imfun_get_users;

create or replace function imfun_get_users(
    _query varchar,
    _page int,
    _size int
)
returns table(
    id uuid,
    name varchar,
    email varchar,
    updated_at timestamptz
) 
language plpgsql
as $$
declare
    _offset int := (_page - 1) * _size;
begin
    return query
    select
        u.id,
        u.name,
        u.email,
        u.updated_at
    from
        users u
    where
        case when _query is null then true else u.name ilike '%' || _query || '%' end
    order by
        u.updated_at desc
    limit
        _size
    offset
        _offset;
end;
$$;



