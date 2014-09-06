$(document).ready(function() {

    // extract parameters for sources and wa_key:
    // NOTE: need to also provide prios so we can sequence
    // submissions accordingly
    var pmap = {
        wa_key: $("param#wa-key").attr("value"),
        search_str: $("param#search-str").attr("value"),
        match_score: $("param#match-score").attr("value"),
        min_wc: $("param#min-wc").attr("value"),
        back_days: $("param#back-days").attr("value")
    };
    var cat_src = {};
    var params = $("param.cat-src");
    for (var i = 0; i < params.length; i++) {
        var cat = params.eq(i).attr("name");
        cat_src[cat] = params.eq(i).attr("value").split(' ');
    }

    // set up "score board"
    var score_board = {};
    var score_board_size = 0;
    for (cat in cat_src) {
        var num_src = cat_src[cat].length;
        for (var i = 0; i < num_src; i++) {
            score_board[cat_src[cat][i]] = {
                'cat': cat,
                'job_id': null,
                'status': 0,    // 1: submitted, got job_id
                                // 2: have result
                                // 3: published
                'result': null
            };
            score_board_size++;
        }
    }
    var score_board_fill = 0;

    // intial call: submit parameters and get job-id:
    for (var src in score_board) {
        pmap['src'] = src;
        $.ajax({
            url: 'scorematches',
            data: pmap,
            type: 'GET',
            dataType: 'json',
            success: function(json) {
                score_board[json.src].job_id = json.job_id;
                score_board[json.src].status = 1;
            },
            eror: function(xhr, status, errorThrown) {
                console.log("Error: " + errorThrown);
                console.log("Status: " + status);
                console.dir(xhr);
            },
            complete: function(xhr, status) {
                console.log("submitted: " + xhr.responseText);
            }
        });
    }

    // now check for results:
    function pollForID(src) {
        return function() {
            var fetch_timeout = 500;
            if (score_board[src].status == 0) {
                setTimeout(pollForID(src), fetch_timeout);
            }
            else {
                $.ajax({
                    url: 'scorematches',
                    data: {'src': src, 'job_id': score_board[src].job_id},
                    type: 'GET',
                    dataType: 'json',
                    success: function(json) {
                        if (json.status == 'finished') {
                            score_board[json.src].status = 2;
                            score_board[json.src].result = json.result;
                        }
                        else {
                            var timeout = fetch_timeout + 2000 * (1 - score_board_fill);
                            setTimeout(pollForID(src), timeout);
                        }
                    },
                    eror: function(xhr, status, errorThrown) {
                        console.log("Error: " + errorThrown);
                        console.log("Status: " + status);
                        console.dir(xhr);
                    },
                    complete: function(xhr, status) {
                        console.log("fetched: " + xhr.responseText);
                    }
                });
            }
        };
    }

    for (var src in score_board) {
        setTimeout(pollForID(src), 1000);
    }

    function insert_result(res_src) {
        var res_cat = score_board[res_src].cat;
        var res_score = parseInt(score_board[res_src].result, 10);
        var position = 0;
        for (var src in score_board) {
            var sbs = score_board[src];
            if (sbs.cat == res_cat && sbs.status == 3) {
                if (parseInt(sbs.result, 10) <= res_score) {
                    ++position;
                }
            }
        }
        console.log("insert_results: " + res_src + " " + res_score + " " + position);
        if (position == 0) {
            $("ul#" + res_cat + "-match").append(
                    "<li>" + res_src + ": " + res_score + "</li>");
        }
        else {
            $("ul#" + res_cat + "-match li").eq(position - 1).after(
                    "<li>" + res_src + ": " + res_score + "</li>");
        }
    }

    // check score board:
    function keep_score() {
        for (var src in score_board) {
            if (score_board[src].status == 2) {
                ++fin_count;
                insert_result(src);
                score_board[src].status = 3;
            }
        }
        score_board_fill = fin_count / score_board_size;
        if (fin_count < score_board_size) {
            var timeout = 1000 + 2000 * (1 - score_board_fill);
            console.log("fin_count: " + fin_count);
            console.log("setting keep_score timeout to " + timeout + "ms");
            setTimeout(keep_score, timeout);
        }
    }
    var fin_count = 0;
    setTimeout(keep_score, 3000);

});

