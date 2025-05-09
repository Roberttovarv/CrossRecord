PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password VARCHAR(25) NOT NULL, 
	is_premium BOOLEAN NOT NULL, 
	name VARCHAR(20) NOT NULL, 
	last_name VARCHAR(20) NOT NULL, 
	username VARCHAR(20) NOT NULL, 
	weight NUMERIC(5, 2), 
	profile_picture VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);
INSERT INTO users VALUES(1,'b@b.com','Robert94*',0,'bea','benitez','bb',64,NULL);
CREATE TABLE calisthenic_exercises (
	id INTEGER NOT NULL, 
	exercise_name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE cardio_exercises (
	id INTEGER NOT NULL, 
	exercise_name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE weighted_exercises (
	id INTEGER NOT NULL, 
	exercise_name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE calisthenic_exercise_variations (
	id INTEGER NOT NULL, 
	variation_name VARCHAR(50) NOT NULL, 
	exercise_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(exercise_id) REFERENCES calisthenic_exercises (id)
);
CREATE TABLE cardio_exercise_variations (
	id INTEGER NOT NULL, 
	variation_name VARCHAR(50) NOT NULL, 
	exercise_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(exercise_id) REFERENCES cardio_exercises (id)
);
CREATE TABLE weighted_exercise_variations (
	id INTEGER NOT NULL, 
	variation_name VARCHAR(50) NOT NULL, 
	exercise_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(exercise_id) REFERENCES weighted_exercises (id)
);
CREATE TABLE follow (
	user_id INTEGER NOT NULL, 
	following_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, following_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(following_id) REFERENCES users (id)
);
CREATE TABLE calisthenic_record (
	id INTEGER NOT NULL, 
	repetitions INTEGER NOT NULL, 
	date DATE NOT NULL, 
	is_a_challenge BOOLEAN NOT NULL, 
	user_id INTEGER NOT NULL, 
	variation_id INTEGER NOT NULL, 
	bodyweight NUMERIC(5, 2), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(variation_id) REFERENCES calisthenic_exercise_variations (id)
);
CREATE TABLE cardio_record (
	id INTEGER NOT NULL, 
	calories NUMERIC(3, 1) NOT NULL, 
	time INTEGER NOT NULL, 
	date DATE NOT NULL, 
	is_a_challenge BOOLEAN NOT NULL, 
	user_id INTEGER NOT NULL, 
	variation_id INTEGER NOT NULL, 
	bodyweight NUMERIC(5, 2), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(variation_id) REFERENCES cardio_exercise_variations (id)
);
CREATE TABLE weight_record (
	id INTEGER NOT NULL, 
	lifted_weight NUMERIC(5, 2) NOT NULL, 
	date DATE NOT NULL, 
	is_a_challenge BOOLEAN NOT NULL, 
	user_id INTEGER NOT NULL, 
	variation_id INTEGER NOT NULL, 
	bodyweight NUMERIC(5, 2), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(variation_id) REFERENCES weighted_exercise_variations (id)
);
CREATE TABLE cardio_challenge (
	id INTEGER NOT NULL, 
	variation_id INTEGER NOT NULL, 
	challenger_id INTEGER NOT NULL, 
	challenged_id INTEGER NOT NULL, 
	record_to_complete INTEGER NOT NULL, 
	message VARCHAR(50), 
	date DATE NOT NULL, 
	is_completed BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(variation_id) REFERENCES cardio_exercise_variations (id), 
	FOREIGN KEY(challenger_id) REFERENCES users (id), 
	FOREIGN KEY(challenged_id) REFERENCES users (id)
);
CREATE TABLE calisthenic_challenge (
	id INTEGER NOT NULL, 
	variation_id INTEGER NOT NULL, 
	challenger_id INTEGER NOT NULL, 
	challenged_id INTEGER NOT NULL, 
	record_to_complete INTEGER NOT NULL, 
	message VARCHAR(50), 
	date DATE NOT NULL, 
	is_completed BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(variation_id) REFERENCES calisthenic_exercise_variations (id), 
	FOREIGN KEY(challenger_id) REFERENCES users (id), 
	FOREIGN KEY(challenged_id) REFERENCES users (id)
);
CREATE TABLE weighted_challenge (
	id INTEGER NOT NULL, 
	variation_id INTEGER NOT NULL, 
	challenger_id INTEGER NOT NULL, 
	challenged_id INTEGER NOT NULL, 
	record_to_complete INTEGER NOT NULL, 
	message VARCHAR(50), 
	date DATE NOT NULL, 
	is_completed BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(variation_id) REFERENCES weighted_exercise_variations (id), 
	FOREIGN KEY(challenger_id) REFERENCES users (id), 
	FOREIGN KEY(challenged_id) REFERENCES users (id)
);
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
COMMIT;
