-- Run only after selecting an isolated test database, for example book_manage_test_demo.
IF OBJECT_ID(N'dbo.books', N'U') IS NULL
CREATE TABLE dbo.books (
    book_id INT IDENTITY(1,1) PRIMARY KEY,
    book_name NVARCHAR(100) NOT NULL,
    author NVARCHAR(50) NULL,
    category NVARCHAR(30) NULL,
    stock INT NOT NULL CONSTRAINT df_books_stock DEFAULT 0,
    update_time DATETIME2 NOT NULL CONSTRAINT df_books_update DEFAULT SYSDATETIME(),
    CONSTRAINT ck_books_stock_nonnegative CHECK (stock >= 0)
);

IF OBJECT_ID(N'dbo.readers', N'U') IS NULL
CREATE TABLE dbo.readers (
    reader_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(50) NOT NULL,
    gender NVARCHAR(10) NULL,
    phone NVARCHAR(20) UNIQUE,
    reg_date DATETIME2 NOT NULL CONSTRAINT df_readers_reg DEFAULT SYSDATETIME(),
    update_time DATETIME2 NOT NULL CONSTRAINT df_readers_update DEFAULT SYSDATETIME()
);

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
CREATE TABLE dbo.users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(20) NOT NULL UNIQUE,
    password NVARCHAR(32) NOT NULL,
    role NVARCHAR(10) NOT NULL,
    create_time DATETIME2 NOT NULL CONSTRAINT df_users_create DEFAULT SYSDATETIME(),
    update_time DATETIME2 NOT NULL CONSTRAINT df_users_update DEFAULT SYSDATETIME()
);

IF OBJECT_ID(N'dbo.borrows', N'U') IS NULL
CREATE TABLE dbo.borrows (
    borrow_id INT IDENTITY(1,1) PRIMARY KEY,
    book_id INT NOT NULL,
    reader_id INT NOT NULL,
    borrow_date DATETIME2 NOT NULL CONSTRAINT df_borrows_borrow DEFAULT SYSDATETIME(),
    return_date DATETIME2 NULL,
    is_overdue BIT NOT NULL CONSTRAINT df_borrows_overdue DEFAULT 0,
    update_time DATETIME2 NOT NULL CONSTRAINT df_borrows_update DEFAULT SYSDATETIME(),
    CONSTRAINT fk_borrows_book FOREIGN KEY (book_id) REFERENCES dbo.books(book_id) ON DELETE CASCADE,
    CONSTRAINT fk_borrows_reader FOREIGN KEY (reader_id) REFERENCES dbo.readers(reader_id) ON DELETE CASCADE
);

IF OBJECT_ID(N'dbo.sync_logs', N'U') IS NULL
CREATE TABLE dbo.sync_logs (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    db_name NVARCHAR(20) NOT NULL,
    op_type NVARCHAR(10) NOT NULL,
    sync_status NVARCHAR(10) NOT NULL,
    is_conflict BIT NOT NULL CONSTRAINT df_sync_conflict DEFAULT 0,
    conflict_desc NVARCHAR(200) NULL,
    sync_time DATETIME2 NOT NULL CONSTRAINT df_sync_time DEFAULT SYSDATETIME()
);
