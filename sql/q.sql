
-- Part C

-- Query to find all content shared with David

select distinct name
from content natural join share natural join member
where member = 'DD';

-- distinct is required, since David may be in more than one group
-- that a content item is shared with.
