CREATE TABLE logs (
    [id] INT IDENTITY(1,1) PRIMARY KEY,
    [date] DATETIME,
    [content] NVARCHAR(MAX),
    player_id INT,
    FOREIGN KEY (player_id) REFERENCES players([id])
);
