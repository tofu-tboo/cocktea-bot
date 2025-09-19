const bot = BotManager.getCurrentBot();

var Jsoup = org.jsoup.Jsoup;
var Method = org.jsoup.Connection.Method;

function onMessage(msg) {
  const { content, author, reply } = msg;
  const sender = author.name;

  if (!content.startsWith("!") || content.length <= 2) {
    // 명령어가 아니거나 단순 느낌표면 무시
    return;
  }

  var command = content.trim().split(" ")[0].slice(1).toLowerCase().trim();
  const recipe_commands = ["레시피", "recipe", "r"];
  const use_commands = ["사용", "use", "u"];

  if (!recipe_commands.includes(command) && !use_commands.includes(command)) {
    command = content.trim().split("\n")[0].slice(1).toLowerCase().trim();
  }

  switch (command) {
    case recipe_commands[0]:
    case recipe_commands[1]:
    case recipe_commands[2]:
      {
        var cocktail_name = content
          .trim()
          .slice(command.length + 1)
          .trim();
        var res = sendReq("recipe/" + cocktail_name, "GET");
        var json = JSON.parse(res.body);
        if (res.succeed) {
          botReply(
            reply,
            json.cocktail_name +
              " 레시피" +
              "\n" +
              json.ingredients +
              "\n\n" +
              json.recipe
          );
        } else {
          var message = json.message;

          botReply(reply, message);
        }
      }
      break;
    case use_commands[0]:
    case use_commands[1]:
    case use_commands[2]:
      {
        var data = content
          .trim()
          .slice(command.length + 1)
          .trim();
        var res = sendReq("update-stock", "PATCH", data);
        var json = JSON.parse(res.body);

        if (res.succeed) {
          botReply(reply, "업데이트 완료.");
          if (json.admin_message) {
            botReply(reply, json.admin_message);
          }
        } else {
          var message = json.message;

          botReply(reply, message);
        }
      }
      break;
  }
}

bot.addListener(Event.MESSAGE, onMessage);

function botReply(reply, content) {
  reply("[봇] " + content);
}

function sendReq(url, method_string, data) {
  var conn = org.jsoup.Jsoup.connect(
    "https://cocktea-bot.vercel.app/api/" + url + "/"
  )
    .ignoreContentType(true)
    .ignoreHttpErrors(true)
    .timeout(10000)
    .header("Content-Type", "application/json");
  const method = {
    GET: org.jsoup.Connection.Method.GET,
    POST: org.jsoup.Connection.Method.POST,
    PATCH: org.jsoup.Connection.Method.PATCH,
    DELETE: org.jsoup.Connection.Method.DELETE,
  }[method_string];

  var res;
  if (method_string == "GET" || method_string == "DELETE") {
    res = conn.method(method).execute();
  } else {
    res = conn
      .method(method)
      .requestBody(JSON.stringify({ content: data }))
      .execute();
  }
  return {
    status: res.statusCode(),
    body: res.body(),
    succeed: res.statusCode() >= 200 && res.statusCode() < 300,
  };
}
