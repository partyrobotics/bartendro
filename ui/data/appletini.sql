insert into drink_name (id, name, sortname, is_common) values (1, "Sour Apple Martini", "Sour Apple Martini", 1);
insert into drink (id, name_id, desc) values (1, 1, 'A sweet apple flavored martini.');
insert into liquid (id, name, desc, abv) values (1, 'Vodka', 'Vodka made from grains with no flavors', 30);
insert into liquid (id, name, desc, abv) values (2, 'Sour Apple Mix', 'Sour Apple Martini mixer.', 15);
insert into drink_liquid (id, drink_id, liquid_id, value, unit) values (1, 1, 1, 1, 1);
insert into drink_liquid (id, drink_id, liquid_id, value, unit) values (2, 1, 2, 1, 1);
