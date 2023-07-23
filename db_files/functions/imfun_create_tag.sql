drop function if exists imfun_create_tag;

create or replace function imfun_create_tag(
    _name varchar
) returns void
language plpgsql
as $$
begin

    insert into tags (name)
    values (_name);

end ;
$$;