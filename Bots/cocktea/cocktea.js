const bot = BotManager.getCurrentBot();

var Jsoup = org.jsoup.Jsoup;
var Method = org.jsoup.Connection.Method;

function onCommand(msg) {
  const { content, author, reply, command, args } = msg;
  const sender = author.name;

  if (content.startsWith("!") && content.length > 1) {
    var conn = org.jsoup.Jsoup.connect(
      "https://cocktea-q9gfln6cj-dgist2023choidoyuns-projects.vercel.app/api/update-stock/"
    )
      .ignoreContentType(true)
      .timeout(10000)
      .header("Content-Type", "application/json");

    var res = conn
      .method(org.jsoup.Connection.Method.PATCH)
      .requestBody(JSON.stringify({ content: content.slice(1) }))
      .execute();

    var code = res.statusCode();
    // 서버 정책에 맞춰 성공 코드 범위 조정 (200/201/204 등)
    if (code >= 200 && code < 300) {
      reply(
        sender +
          "님, 노션 수정 요청이 처리되었습니다.\n확인요망: https://www.notion.so/26c968085ab980369fcfff8902d3927e"
      );
    } else {
      reply("요청 실패(code: " + code + ")\n" + res.body());
    }
  }
}

bot.setCommandPrefix("!");
bot.addListener(Event.COMMAND, onCommand);
