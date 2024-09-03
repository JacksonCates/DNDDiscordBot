CREATE TABLE players (
    [id] INT IDENTITY(1,1) PRIMARY KEY,
    [name] VARCHAR(255),
    [player_name] VARCHAR(255),
    [role] VARCHAR(50)
);

INSERT INTO players ([name], player_name, [role]) VALUES
('mrfrknfantastic', 'Faelen Shadowfeather', 'player'),
('cadoon22', 'Malakar Darkheart', 'player'),
('questioningdecisions', 'Flint Forger', 'player'),
('theonerottenegg', 'Jose Bergeron', 'player'),
('yaboisaltin', 'DM', 'DM')