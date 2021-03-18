create table web.user
(
	uid int auto_increment
		primary key,
	initialid varchar(31) not null,
	constraint user_initialid_uindex
		unique (initialid)
);

create table web.user_search
(
	uid int not null,
	query varchar(255) null,
	constraint user_search_user_uid_fk
		foreign key (uid) references web.user (uid)
);

create table if not exists web.user_time
(
	uid int not null,
	timeminutes int not null,
	constraint user_time_user_uid_fk
		foreign key (uid) references web.user (uid)
);

create table web.user_url
(
	uid int not null,
	url varchar(255) null,
	constraint user_url_user_uid_fk
		foreign key (uid) references web.user (uid)
);


/**
  获取用户搜索排名的 SQL
*/
select u.initialid, us.ucount from web.user u inner join
(select us.uid, count(*) as ucount from user_search us group by uid order by ucount desc LIMIT 20) as us
on u.uid = us.uid;

/**
  获取用户搜索关键词的 SQL
 */
select us.query from web.user_search us inner join web.user u on us.uid = u.uid where u.initialid = '8794463366737124';

/**
  根据关键词反查用户和次数 <- 会稍微慢一点，因为 query 上用了 like 查询，索引会失效
 */
select us.uid, u.initialid, count(*) as scount from web.user_search us join user u on u.uid = us.uid where us.query like '%中国%' group by us.uid, u.initialid order by scount desc;

/**
  查询用户的上网时间
 */
select ut.timeminutes from web.user_time ut inner join web.user u on u.uid = ut.uid where u.initialid = '8794463366737124';

/**
  查询用户访问的 URL
 */

select uu.url, count(*) as ucount from web.user_url uu inner join web.user u on u.uid = uu.uid where u.initialid = '8794463366737124' group by uu.url order by ucount desc;