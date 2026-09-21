-- Synthetic test data. Password values are test-only MD5 hashes.
BEGIN;
DELETE FROM borrows WHERE book_id IN (SELECT book_id FROM books WHERE book_name LIKE 'QA_PUBLIC_%');
DELETE FROM books WHERE book_name LIKE 'QA_PUBLIC_%';
DELETE FROM readers WHERE name LIKE 'QA_PUBLIC_%';
DELETE FROM users WHERE username LIKE 'qa_public_%';

INSERT INTO users (username, password, role) VALUES
('qa_public_admin', md5('Admin-Test-Only-01'), '管理员'),
('qa_public_operator', md5('Operator-Test-Only-01'), '操作员'),
('qa_public_viewer', md5('Viewer-Test-Only-01'), '查看员');

INSERT INTO books (book_name, author, category, stock) VALUES
('QA_PUBLIC_NORMAL', 'QA_AUTHOR', 'QA_CATEGORY', 2),
('QA_PUBLIC_ZERO', 'QA_AUTHOR', 'QA_CATEGORY', 0),
('QA_PUBLIC_LAST_COPY', 'QA_AUTHOR', 'QA_CATEGORY', 1);

INSERT INTO readers (name, gender, phone) VALUES
('QA_PUBLIC_READER_A', '其他', '10000000001'),
('QA_PUBLIC_READER_B', '其他', '10000000002');
COMMIT;
