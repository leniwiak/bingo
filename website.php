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
			<?php
			if (isset($_GET['s'])) {
				$search = $_GET['s'];
			} else {
				$search = "";
			};
				
			echo "<input type=\"text\" name=\"s\" required max=\"169\" id=\"inputbox\" value=\"".$search."\">";
			?>
			<input type="submit" value="Search">
		</form>
	</header>

	<script>
		// This function takes two arguments: search_id (Search result ID to manage) and action (like or dislike).
		// Then, it connects to add_opinion.php and gives opinion to a proper search result
		function add_opinion(search_id, action) {
			console.log(action);
			const xhttp = new XMLHttpRequest();
			xhttp.onload = function() {
				const pstro = parseInt(document.getElementById(action).text);
				document.getElementById(action).innerHTML = pstro+1;
			}
			xhttp.open("GET", "add_opinion.php?action="+action+"&id="+search_id, true);
			xhttp.send();
		}
		var items = Array("What's on your mind?", "Anything interesting?", "Type something here", "A query of the day is...", "Describe your intentions", "Search the internet", "What's going on?", "What do you like?", "Tell me what to do", "What you want to discover?", "Anywhere to go?", "Let's surf!", "Let's start!", "Browse the web");
		var item = items[Math.floor(Math.random()*items.length)];
		document.getElementById("inputbox").placeholder = item;
	</script>

	<main>
		<?php
		if (isset($_GET['s'])) {
			$search = $_GET['s'];
			if (strlen($search) < 3) {
				echo "<h2>Oopsie!</h2>";
				echo "<p>Try typing more than two letters, please.</p>";
				die();
			};
			if (strlen($search) > 169) {
				echo "<h2>Oopsie!</h2>";
				echo "<p>You request exceeds allowed text length! Please, make your query a bit shorter.</p>";
				die();
			};
			$db = new SQLite3("./searchindex.db");
			$result = $db -> query("SELECT DISTINCT id, title, desc, link, like, dislike FROM searches WHERE ".
					"title LIKE '%".$search."%' OR desc LIKE '%".$search."%' OR link LIKE '%".$search."%'");

			echo "<table>";
			while ($row = $result -> fetchArray()) {
				echo "<tr>";
					echo "<td id=\"web_result\">";
					echo "<a href=\"".$row['link']."\">";
						if($row['title']!="") {
							echo "<h2>".$row['title']."</h2>";
						} else {
							$temporary_title = substr(stristr($row['link'], "://"), 3);
							echo "<h2>".$temporary_title."</h2>";
						}
						echo "<a href=\"".$row['link']."\" id=\"url\">".$row['link']."</a>";
						if($row['desc']!="") {
							echo "<p>".$row['desc']."</p>";
						} else {
							echo "<p>Sorry. No description provided.</p>";
						}
					echo "</a>";
					echo "<br>";

					echo "<div id=\"reaction\" onclick=\"add_opinion(".$row['id'].", 'like');\">";
						echo "<svg align=\"left\" xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 -960 960 960\" width=\"1.5%\"><path d=\"M720-120H280v-520l280-280 50 50q7 7 11.5 19t4.5 23v14l-44 174h258q32 0 56 24t24 56v80q0 7-2 15t-4 15L794-168q-9 20-30 34t-44 14Zm-360-80h360l120-280v-80H480l54-220-174 174v406Zm0-406v406-406Zm-80-34v80H160v360h120v80H80v-520h200Z\" id=\"reaction_svg\"/></svg>";
						echo "<a id=\"like\" class=\"reaction_count\">".$row['like']."</a>";
					echo "</div>";

					echo "<div id=\"reaction\" onclick=\"add_opinion(".$row['id'].", 'dislike');\">";
						echo "<svg align=\"left\" xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 -960 960 960\" width=\"1.5%\"><path d=\"M240-840h440v520L400-40l-50-50q-7-7-11.5-19t-4.5-23v-14l44-174H120q-32 0-56-24t-24-56v-80q0-7 2-15t4-15l120-282q9-20 30-34t44-14Zm360 80H240L120-480v80h360l-54 220 174-174v-406Zm0 406v-406 406Zm80 34v-80h120v-360H680v-80h200v520H680Z\" id=\"reaction_svg\"/></svg>";
						echo "<a id=\"dislike\" class=\"reaction_count\">".$row['dislike']."</a>";
					echo "</div>";

					echo "</td>";
				echo "</tr>";
			}
			echo "</table>";
		};
		?>
	</main>
</body>
</html>
