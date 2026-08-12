🗄️ NoSQL Skills
Skill	Cần biết gì?
1. Data Modeling	Thiết kế schema theo access pattern, tránh duplicate dữ liệu không cần thiết
2. Query Optimization	limit, pagination, filter, sort, giảm số document/data phải đọc
3. Indexing	Thiết kế composite index phù hợp với các query thường xuyên
4. Aggregation	Biết khi nào dùng count/sum/average, khi nào dùng precomputed/write-time aggregation
5. Read vs Write Optimization	Đánh đổi giữa tính toán lúc đọc và cập nhật sẵn lúc ghi
6. N+1 Query Prevention	Phát hiện và loại bỏ chuỗi query tuần tự không cần thiết
7. Parallel Query Execution	Chạy các query độc lập song song để giảm latency
8. Caching Strategy	Biết khi nào dùng Redis/cache và cách invalidation
9. Realtime Data Sync	Snapshot listener, realtime update, SSE/WebSocket và consistency
10. Data Consistency	Idempotency, transaction, duplicate prevention, retry
11. Cost Optimization	Tối ưu số lượng document read/write và kích thước dữ liệu
12. Scalability	Thiết kế database để vẫn hoạt động tốt khi dữ liệu/user tăng
P0

Data Modeling theo Access Pattern
Query + Index Optimization
Pagination + Limit
N+1 Query Prevention
Parallel Query Execution

P1

Aggregation / Precomputed Summary
Redis Cache + Cache Invalidation