<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Bingo!</title>
	<link rel="stylesheet" type="text/css" href="for_me_you_have_stajla.css">
</head>
</body>
	<header>
		<h1>Bingo!</h1>
		<form method="get">
			<input type="text" name="s" required max="169" placeholder="What's on your mind?">
			<input type="submit" value="Search">
		</form>
	</header>
	<main>
		<?php
		if (isset($_GET['s'])) {
			$search = $_GET['s'];
			if (strlen($search) < 3) {
				echo "<h2>Oopsie!</h2>";
				echo "<p>Try typing more than two letters, please.</p>"
				die();
			};
			if (strlen($search) > 169) {
				echo "<h2>Oopsie!</h2>";
				echo "<p>You request exceeds allowed text length! Please, make your query a bit shorter.</p>"
				die();
			};
			$db = new SQLite3("./searchindex.db");
			$result = $db -> query("SELECT DISTINCT title, desc, link FROM searches WHERE ".
					"title LIKE '%".$search."%' OR desc LIKE '%".$search."%' OR link LIKE '%".$search."%'");

			echo "<table>";
			while ($row = $result -> fetchArray()) {
				echo "<tr>";
					echo "<td id=\"web_result\">";
					echo "<a href=\"".$row['link']."\">";
						echo "<h2>".$row['title']."</h2>";
						echo "<a href=\"".$row['link']."\" id=\"url\">".$row['link']."</a>";
						echo "<p>".$row['desc']."</p>";
					echo "</a>";
					echo "</td>";
				echo "</tr>";
			}
			echo "</table>";
		};
		?>
	</main>
</body>
</html>
