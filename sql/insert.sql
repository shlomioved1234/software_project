
--Part B

insert into person(uname, password, fname, lname) values
('AA', md5('AA'), 'Ann', 'Anderson'),
('BB', md5('BB'), 'Bob', 'Baker'),
('CC', md5('CC'), 'Cathy', 'Chang'),
('DD', md5('DD'), 'David', 'Davidson'),
('EE', md5('EE'), 'Ellen', 'Ellenberg'),
('FF', md5('FF'), 'Fred', 'Fox'),
('GG', md5('GG'), 'Gina', 'Gupta'),
('HH', md5('HH'), 'Helen', 'Harper');

insert  into friendgroup(owner, gname) values
('AA', 'family'),
('BB', 'family'),
('AA', 'besties');

insert into member(owner, gname, member) values
('AA', 'family', 'AA'),
('AA', 'family', 'CC'),
('AA', 'family', 'DD'),
('AA', 'family', 'EE'),
('BB', 'family', 'BB'),
('BB', 'family', 'FF'),
('BB', 'family', 'EE'),
('AA', 'besties', 'AA'),
('AA', 'besties', 'GG'),
('AA', 'besties', 'HH');

insert into content(cid, uname, name, is_pub) values
(1, 'AA', 'Whiskers', false),
(2, 'AA', 'My birthday party', false),
(3, 'BB', 'Rover', false);

insert into share(cid, owner, gname) values
(1, 'AA', 'family'),
(2, 'AA', 'besties'),
(3, 'BB', 'family');
