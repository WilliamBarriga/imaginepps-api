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


insert into user_groups (name) values ('admin'), ('free_user'), ('premium_user'), ('author');

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
	 ('auth/validate','OPTIONS',true)
     ('/users','GET',true),
	 ('/users','OPTIONS',true),
     ('/users/#','GET',true),
     ('/users/#','PATCH',true),
     ('/users/#','OPTIONS',true),


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
	 (4,4);


create table logs (
    id bigserial primary key,
    user_id uuid null references users(id),
    route_permission_id bigint null references routes_permissions(id),
    request jsonb null,
    response jsonb null,
    user_data jsonb null,
    created_at timestamptz not null default now()
);
