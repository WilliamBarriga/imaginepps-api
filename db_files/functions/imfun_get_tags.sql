drop function if exists imfun_get_tags(varchar, integer, integer);

create or replace function imfun_get_tags(
    _query varchar,
    _page integer,
    _page_size integer
) returns table (
    id bigint,
    name varchar
)
language plpgsql
as $$

declare
    _offset integer := (_page - 1) * _page_size;

begin

    return query
    select
        t.id,
        t.name
    from
        tags t
    where
        case
            when _query is not null then
                t.name ilike '%' || _query || '%'
            else
                true
        end
    order by
        t.name
    limit
        _page_size
    offset
        _offset;

end ;
$$;