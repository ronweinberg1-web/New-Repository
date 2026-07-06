use tech

create view Schedule_view as
select t.*, CAST(date AS datetime) + CAST(time AS datetime) AS CombinedDateTime
from dbo.Schedule t
where position='Python Dev'
and available=1;


UPDATE Schedule
SET date = DATEADD(year, 2, date);