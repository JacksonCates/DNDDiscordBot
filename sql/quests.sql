CREATE TABLE quests (
    [id] INT IDENTITY(1,1) PRIMARY KEY,
    [title] NVARCHAR(MAX),
    [status] NVARCHAR(MAX),
    [content] NVARCHAR(MAX),
    is_deleted BIT
);

--ALTER TABLE quests
--ADD is_deleted BIT DEFAULT 0


CREATE TABLE player_quests (
    [quest_id] INT,
    [player_id] INT,
    FOREIGN KEY (quest_id) REFERENCES [quests]([id]),
    FOREIGN KEY (player_id) REFERENCES [players]([id])
)