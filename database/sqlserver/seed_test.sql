-- Synthetic test data. HASHBYTES creates test-only MD5 values used by the demo app.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
DELETE b FROM dbo.borrows b JOIN dbo.books k ON b.book_id = k.book_id WHERE k.book_name LIKE N'QA_PUBLIC_%';
DELETE FROM dbo.books WHERE book_name LIKE N'QA_PUBLIC_%';
DELETE FROM dbo.readers WHERE name LIKE N'QA_PUBLIC_%';
DELETE FROM dbo.users WHERE username LIKE N'qa_public_%';

INSERT INTO dbo.users (username, password, role) VALUES
(N'qa_public_admin', LOWER(CONVERT(VARCHAR(32), HASHBYTES('MD5', 'Admin-Test-Only-01'), 2)), N'管理员'),
(N'qa_public_operator', LOWER(CONVERT(VARCHAR(32), HASHBYTES('MD5', 'Operator-Test-Only-01'), 2)), N'操作员'),
(N'qa_public_viewer', LOWER(CONVERT(VARCHAR(32), HASHBYTES('MD5', 'Viewer-Test-Only-01'), 2)), N'查看员');

INSERT INTO dbo.books (book_name, author, category, stock) VALUES
(N'QA_PUBLIC_NORMAL', N'QA_AUTHOR', N'QA_CATEGORY', 2),
(N'QA_PUBLIC_ZERO', N'QA_AUTHOR', N'QA_CATEGORY', 0),
(N'QA_PUBLIC_LAST_COPY', N'QA_AUTHOR', N'QA_CATEGORY', 1);

INSERT INTO dbo.readers (name, gender, phone) VALUES
(N'QA_PUBLIC_READER_A', N'其他', N'10000000001'),
(N'QA_PUBLIC_READER_B', N'其他', N'10000000002');
COMMIT TRANSACTION;
