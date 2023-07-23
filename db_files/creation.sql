CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

create or replace function update_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- Users

create table user_groups (
    id bigserial primary key,
    name varchar(255) not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    active boolean not null default true
);

create trigger update_updated_at
before update on user_groups
for each row
execute procedure update_updated_at();


insert into user_groups (name) values ('admin'), ('free_user'), ('premium_user');

create table users (
    id uuid DEFAULT uuid_generate_v4 () primary key,
    name varchar(255) not null,
    email varchar(255) not null unique,
    password varchar(255) not null,
    group_id bigint not null references user_groups(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    active boolean not null default true
);

create trigger update_updated_at
before update on users
for each row
execute procedure update_updated_at();

create index users_email_index on users (email);

create table routes_permissions (
    id bigserial primary key,
    route varchar(255) not null,
    method varchar(255) not null,
    exclude boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    active boolean not null default true
);

create trigger update_updated_at
before update on routes_permissions
for each row
execute procedure update_updated_at();

INSERT INTO routes_permissions (route,"method","exclude") VALUES
	 ('/auth/me','GET',false),
	 ('/auth/signup','POST',true),
	 ('/auth/login','POST',true),
	 ('/auth/validate','GET',false),
	 ('/auth/me','OPTIONS',true),
	 ('auth/signup','OPTIONS',true),
	 ('auth/login','OPTIONS',true),
	 ('auth/validate','OPTIONS',true),
     ('/users/','GET',true),
	 ('/users/','OPTIONS',true),
     ('/users/#','GET',true),
     ('/users/#','PATCH',false),
     ('/users/#','OPTIONS',true),
     ('/notes/','GET',true),
	 ('/notes/','POST',true),
	 ('/notes/','OPTIONS',true),
	 ('/notes/#','GET',true),
	 ('/notes/#','PATCH',true),
	 ('/notes/#','OPTIONS',true),
	 ('/notes/#/like','POST',true),
	 ('/notes/#/like','OPTIONS',true),
     ('/tags/','GET',true),
	 ('/tags/','POST',true),
	 ('/tags/','OPTIONS',true);


create table user_groups_routes_permissions (
    id bigserial primary key,
    user_group_id bigint not null references user_groups(id),
    route_permission_id bigint not null references routes_permissions(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    active boolean not null default true
);

create trigger update_updated_at
before update on user_groups_routes_permissions
for each row
execute procedure update_updated_at();

INSERT INTO user_groups_routes_permissions (user_group_id,route_permission_id) VALUES
	 (1,1),
	 (2,1),
	 (3,1),
	 (4,1),
	 (1,4),
	 (2,4),
	 (3,4),
	 (4,4),
     (1,12),
     (2,12);


create table logs (
    id bigserial primary key,
    user_id uuid null references users(id),
    route_permission_id bigint null references routes_permissions(id),
    request jsonb null,
    response jsonb null,
    user_data jsonb null,
    created_at timestamptz not null default now()
);

-- Notes

create table notes (
    id bigserial primary key,
    title varchar(255) not null,
    content text not null,
    favorite boolean not null default false,
    user_id uuid not null references users(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    active boolean not null default true
);

create trigger update_updated_at
before update on notes
for each row
execute procedure update_updated_at();

create index notes_user_id_index on notes (user_id);

create table tags (
    id bigserial primary key,
    name varchar(255) not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    active boolean not null default true
);

create trigger update_updated_at
before update on tags
for each row
execute procedure update_updated_at();

create table notes_tags (
    id bigserial primary key,
    note_id bigint not null references notes(id),
    tag_id bigint not null references tags(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    active boolean not null default true
);

create trigger update_updated_at
before update on notes_tags
for each row
execute procedure update_updated_at();

create index notes_tags_note_id_index on notes_tags (note_id);
create index notes_tags_tag_id_index on notes_tags (tag_id);

create table notes_likes (
    id bigserial primary key,
    note_id bigint not null references notes(id),
    user_id uuid not null references users(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    active boolean not null default true
);

create trigger update_updated_at
before update on notes_likes
for each row
execute procedure update_updated_at();

create index notes_likes_note_id_index on notes_likes (note_id);
create index notes_likes_user_id_index on notes_likes (user_id);



































-- functions

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


drop function if exists imfun_create_note;

create or replace function imfun_create_note(
    _title varchar,
    _content varchar,
    _tags varchar[],
    _favorite boolean,
    _user_id uuid
) returns table (
    id bigint,
    title varchar,
    content text,
    favorite boolean,
    "user" jsonb,
    tags jsonb,
    total_likes bigint,
    likes jsonb
)
language plpgsql
as $$

declare
    _note_id bigint;

begin
    insert into notes (title, content, user_id, favorite)
    values (_title, _content, _user_id, _favorite)
    returning notes.id into _note_id;

    insert into notes_tags (note_id, tag_id)
    select _note_id, tags.id
    from tags
    where tags.name = any(_tags);

    return query
        select * from imfun_get_note(_note_id);
end;
$$;

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


drop function if exists imfun_get_note;

create or replace function imfun_get_note(
    _id bigint
) returns table (
    id bigint,
    title varchar,
    content text,
    favorite boolean,
    "user" jsonb,
    tags jsonb,
    total_likes bigint,
    likes jsonb
)
language plpgsql
as $$

begin
    return query
    select n.id, n.title, n."content", n.favorite,
        jsonb_build_object(
            'id', u.id ,
            'name', u."name"
        ) "user",
        jsonb_agg(
            distinct
            jsonb_build_object(
                'id', t.id,
                'name', t."name"
            ) 
        ) tags,
        count(nl.id) total_likes,
        jsonb_agg(
            select 
            jsonb_build_object(
                'id', u2.id,
                'name', u2."name"
            )
            from users u2
            where u2.id = nl.user_id
        ) likes
    from notes n
    join users u on u.id = n.user_id
    left join notes_tags nt on n.id = nt.note_id
    left join tags t on nt.tag_id = t.id
    left join notes_likes nl on nl.note_id = n.id
    where
        n.active = true
        and n.id = _id
    group by n.id, u.id;
end;
$$;


drop function if exists imfun_get_notes;

create or replace function imfun_get_notes(
    _query varchar,
    _page integer,
    _page_size integer,
    _name varchar,
    _tags varchar[],
    _favorites boolean
) returns table (
    id bigint,
    title varchar,
    content text,
    favorite boolean,
    "user" jsonb,
    tags jsonb,
    likes bigint
)
language plpgsql
as $$

declare
    _offset integer := (_page - 1) * _page_size;

begin
    return query
    select n.id, n.title, n."content", n.favorite,
        jsonb_build_object(
            'id', u.id ,
            'name', u."name"
        ) "user",
        jsonb_agg(
            distinct
            jsonb_build_object(
                'id', t.id,
                'name', t."name"
            ) 
        ) tags,
        count(nl.id) likes
    from notes n 
    join users u on u.id = n.user_id 
    left join notes_tags nt on n.id = nt.note_id  
    left join tags t on nt.tag_id = t.id
    left join notes_likes nl on nl.note_id = n.id 
    where
        n.active = true
        and case
            when _query is not null then
                n.title ilike '%' || _query || '%'
            else
                true
        end
        and case
            when _name is not null then
                n.title ilike '%' || _name || '%'
            else
                true
        end
        and case
            when _tags is not null then
                t.name = any(_tags)
            else
                true
        end
        and case
            when _favorites is not null then
                n.favorite = _favorites
            else
                true
        end
    group by n.id, u.id
    order by n.updated_at desc
    limit _page_size
    offset _offset;

end;    
$$;


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
        rp.route = _url
        and rp.method = _method
        and rp.active = true;
    
    if _exclude then
        _permission = true;
    else
        select
            count(*) > 0
            into _permission
        from
            user_groups_routes_permissions ugp
        where
            ugp.user_group_id = _user_group_id
            and ugp.route_permission_id = _permission_id
            and ugp.active = true;
    end if;
end;
$$;


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



drop function if exists imfun_like_note;

create or replace function imfun_like_note(
    _note_id bigint,
    _user_id uuid
) returns void
language plpgsql
as $$

begin
    insert into notes_likes (note_id, user_id)
    values (_note_id, _user_id);
end;
$$;



drop function if exists imfun_patch_note;

create or replace function imfun_patch_note(
    _id bigint,
    _title varchar,
    _content varchar,
    _tags varchar[],
    _favorite boolean,
    _user_id uuid
) returns table (
    id bigint,
    title varchar,
    content text,
    favorite boolean,
    "user" jsonb,
    tags jsonb,
    total_likes integer,
    likes jsonb
)
language plpgsql
as $$

declare
	_tag varchar;
    _tag_id bigint;

begin
    update notes
    set
        title = coalesce(_title, title),
        content = coalesce(_content, content),
        favorite = coalesce(_favorite, favorite)
    where notes.id = _id;

    if _tags is not null then
        update notes_tags
        set active = false
        where notes_tags.note_id = _id;

        for _tag in select * from unnest(_tags) loop
            select tags.id into _tag_id
            from tags
            where tags.name ilike _tag;

            if _tag_id is null then
                insert into tags (name)
                values (_tag);
            else
                update notes_tags
                set active = true
                where notes_tags.note_id = _id
                and notes_tags.tag_id = _tag_id;
            end if;

        end loop;

    end if;
end;
$$;


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
