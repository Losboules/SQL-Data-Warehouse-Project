-- Dialect: PostgreSQL SQL
-- Run in: pgAdmin Query Tool connected to northstar_digital.
SELECT 'web_users' AS table_name, COUNT(*) AS row_count FROM digital.web_users
UNION ALL SELECT 'web_sessions', COUNT(*) FROM digital.web_sessions
UNION ALL SELECT 'web_events', COUNT(*) FROM digital.web_events
UNION ALL SELECT 'campaigns', COUNT(*) FROM digital.campaigns
UNION ALL SELECT 'marketing_spend', COUNT(*) FROM digital.marketing_spend;

SELECT COUNT(*) AS orphan_events
FROM digital.web_events AS e
LEFT JOIN digital.web_sessions AS s ON s.session_id = e.session_id
WHERE s.session_id IS NULL;

SELECT COUNT(*) AS out_of_order_events
FROM digital.web_events AS e
JOIN digital.web_sessions AS s ON s.session_id = e.session_id
WHERE e.event_timestamp < s.session_start_utc;

SELECT source_channel, COUNT(*) AS sessions, COUNT(converted_order_id) AS converted_sessions
FROM digital.web_sessions
GROUP BY source_channel
ORDER BY sessions DESC;
