
-- Project Part 2
-- Group Members: Dov Salomon, Danny Lin, Shlomo Oved

-- Part A

-- Tables:
-- person(uname, password, fname, lname)
	  -----
-- content(cid, uname, date, file_path, name, is_pub)
	   ---
-- comment(uname, cid, timestamp, text)
           -----  ---  ---------
-- tag(tagger, taggee, cid, timestamp, status)
       ------  ------  ---
-- friendgroup(owner, gname, description)
               -----  -----
-- member(owner, gname, member)
          -----  -----  ------
-- share(cid, owner, gname)
         ---  -----  -----

create table if not exists person (
	uname varchar(64) not null,
	password varchar(255) not null,
	fname varchar(60),
	lname varchar(60),
	primary key(uname)
);

create table if not exists content (
	cid int(10) unsigned not null auto_increment,
	uname varchar(64) not null,
	date timestamp default current_timestamp,
	file_path varchar(255) default null,
	name varchar(255) not null,
	is_pub boolean default false,
	primary key(cid),
	foreign key(uname) references person(uname)
);

create table if not exists comment (
	uname varchar(64) not null,
	cid int(10) unsigned not null,
	timestamp timestamp not null default current_timestamp,
	text longtext default null,
	primary key(uname, cid, timestamp),
	foreign key(uname) references person(uname),
	foreign key(cid) references content(cid)
);

create table if not exists tag (
	tagger varchar(64) not null,
	taggee varchar(64) not null,
	cid int(10) unsigned not null,
	timestamp timestamp default current_timestamp,
	status varchar(64),
	primary key(tagger, taggee, cid),
	foreign key(tagger) references person(uname),
	foreign key(tagger) references person(uname),
	foreign key(cid) references content(cid)
);

create table if not exists friendgroup (
	owner varchar(64) not null,
	gname varchar(64) not null,
	description longtext default null,
	primary key(owner, gname),
	foreign key(owner) references person(uname)
);

create table if not exists member (
	owner varchar(64) not null,
	gname varchar(64) not null,
	member varchar(64) not null,
	primary key(owner, gname, member),
	foreign key(owner, gname) references friendgroup(owner, gname),
	foreign key(member) references person(uname)
	-- no need for FK on owner, its already contrained by friendgroup FK
);

create table if not exists share (
	cid int(10) unsigned not null,
	owner varchar(64) not null,
	gname varchar(64) not null,
	primary key(cid, owner, gname),
	foreign key(cid) references content(cid),
	foreign key(owner, gname) references friendgroup(owner, gname)
);
