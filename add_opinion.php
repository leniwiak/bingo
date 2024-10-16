<?php
if(isset($_GET['action']) && isset($_GET['id'])) {
	$action = $_GET['action'];
	$search_id = $_GET['id'];

	$db = new SQLite3("./searchindex.db");
	if ($action == "like") {
		$stmt = $db->prepare("UPDATE searches SET like = like+1 WHERE id=:search_id;");
		$stmt -> bindValue(':search_id', $search_id, SQLITE3_INTEGER);
		$stmt -> execute();
	}
	else if ($action == "dislike") {
		$stmt = $db->prepare("UPDATE searches SET dislike = dislike+1 WHERE id=:search_id;");
		$stmt -> bindValue(':search_id', $search_id, SQLITE3_INTEGER);
		$stmt -> execute();
	}
}
