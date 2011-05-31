insert into drink_name (id, name, sortname, is_common) values (2, "Screwdriver", "Screwdriver", 1);
insert into drink (id, name_id, desc) values (2, 2, 'A sweet apple flavored martini.');
insert into booze (id, name, desc, abv) values (3, 'Orange Juice', 'OJ -- that shit from the trees!', 0);
insert into drink_booze (id, drink_id, booze_id, value, unit) values (3, 2, 3, 1, 1);
insert into drink_booze (id, drink_id, booze_id, value, unit) values (4, 2, 4, 1, 1);
