-- One row per stage entry. Terminal events close the preceding stage.
WITH sequenced AS (
    SELECT change_id, to_status AS stage, timestamp AS entered_at,
           LEAD(timestamp) OVER (PARTITION BY change_id ORDER BY id) AS exited_at
    FROM history
    WHERE julianday(timestamp) <= julianday(:as_of)
), durations AS (
    SELECT stage, exited_at,
           julianday(COALESCE(exited_at, :as_of)) - julianday(entered_at) AS days
    FROM sequenced
    WHERE stage IN ('SUBMITTED', 'IN_REVIEW', 'APPROVED')
)
SELECT stage,
       COUNT(exited_at) AS completed_visits,
       ROUND(AVG(CASE WHEN exited_at IS NOT NULL THEN days END), 1) AS mean_completed_days,
       SUM(CASE WHEN exited_at IS NULL THEN 1 ELSE 0 END) AS open_visits,
       ROUND(MAX(CASE WHEN exited_at IS NULL THEN days END), 1) AS oldest_open_days
FROM durations
GROUP BY stage
ORDER BY CASE stage WHEN 'SUBMITTED' THEN 1 WHEN 'IN_REVIEW' THEN 2 ELSE 3 END;
