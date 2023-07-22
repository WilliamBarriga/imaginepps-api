create or replace function update_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create table logs (
    id bigserial primary key,
    user_id bigint null references users(id),
    request jsonb null,
    response jsonb null,
    user_data jsonb null,
    created_at timestamptz not null default now()
);


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
    id bigserial primary key,
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
