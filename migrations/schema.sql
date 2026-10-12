CREATE TABLE "friendRequests" (
	"sender"	VARCHAR(64),
	"recipient"	VARCHAR(64),
	"expireTimestamp"	INTEGER
);

CREATE TABLE gameStats (uuid, statID, value, version INTEGER);

CREATE TABLE "messages" (
	"sender_uuid"	VARCHAR(64),
	"sender_name"	VARCHAR(64),
	"recipient_uuid"	VARCHAR(64),
	"recipient_name"	VARCHAR(64),
	"content"	VARCHAR(100),
	"timestamp"	INTEGER
);

CREATE TABLE "parties" (
	"ownerUUID"	VARCHAR(64) UNIQUE,
	"players"	JSON,
	"public"	BOOLEAN
);

CREATE TABLE partyInvites (inviter VARCHAR(64), recipient VARCHAR(64), expireTimestamp INTEGER);

CREATE TABLE "punishments" (
	"id"	INTEGER,
	"uuid"	VARCHAR(64),
	"username"	VARCHAR(64),
	"modUUID"	VARCHAR(64),
	"modUsername"	VARCHAR(64),
	"type"	varchar(64),
	"issuedTimestamp"	INTEGER,
	"effectiveUntilTimestamp"	INTEGER,
	"expireTimestamp"	INTEGER,
	"reason"	TEXT,
	"enforced"	BOOLEAN,
	"editorModUsername"	VARCHAR(64),
	"editorModUUID"	VARCHAR(64),
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "requests" (
    "request_id"    TEXT UNIQUE,
    "path"    TEXT,
    "method" TEXT,
    "declared_timestamp" INTEGER,
	"real_timestamp" INTEGER,
    "server_id" TEXT,
    "ip_address" TEXT,
    "request_body" TEXT,
    "status_code" INTEGER,
    "response_body" TEXT
	);

CREATE TABLE "users" (
	"uuid"	VARCHAR(64),
	"username"	VARCHAR(64),
	"server"	VARCHAR(64),
	"online"	BOOLEAN,
	"first_join"	INTEGER,
	"last_join"	INTEGER,
	"last_online"	INTEGER,
	"last_ip"	VARCHAR(64),
	"coins"	INTEGER,
	"xp"	INTEGER,
	"playtime"	INTEGER,
	"timezone"	VARCHAR(64),
	"vanish"	BOOLEAN,
	"message_privacy"	VARCHAR(32),
	"ignore_list"	LIST,
	"chat_channel"	VARCHAR(32),
	"friends"	LIST,
	"chat_tag"	VARCHAR(1000),
	"owned_cosmetics"	LIST,
	"equipped_cosmetics"	LIST,
	"custom_rankplate"	VARCHAR(1000),
	"level"	INTEGER,
	"chat_color"	VARCHAR(64),
	"nickname"	VARCHAR(64),
	"muted_channels"	LIST,
	"friend_request_privacy"	VARCHAR(64),
	"party_invite_privacy"	VARCHAR(64),
	"ranks"	LIST, version INTEGER,
	PRIMARY KEY("uuid")
);

CREATE TABLE "schema_version" ("key" TEXT, "value" INTEGER NOT NULL);
INSERT INTO schema_version (key, value) VALUES ('version', 0);