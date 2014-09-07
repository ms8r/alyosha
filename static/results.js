$(document).ready(function() {

    // extract parameters for sources and wa_key:
    // NOTE: need to also provide prios so we can sequence
    // submissions accordingly (or pre-sort params within cat)
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
    for (var cat in cat_src) {
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
                            console.dir(json.result)
                        }
                        else {
                            var timeout = fetch_timeout +
                                          2000 * (1 - score_board_fill);
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
/*

    // setup results by category:
    var cat_res = {};
    for (var cat in cat_src) {
        cat_res[cat] = [];
    }

    function compare_score(a, b) {
        // a and b will be elements of one of cat_res' result lists
        return b.score- a.score;
    }

    function insert_result(res_src) {
        var rsb = score_board[res_src];
        cat_res[rsb.cat].push(
                {'src': res_src,
                 'score': rsb.result
                });  // will ned to be extended to handle list of results
        cat_res[rsb.cat].sort(compare_score);
        //now update HTML:
        cat_html = "";
        num_res = cat_res[rsb.cat].length;
        for (var i = 0; i < num_res; i++ ) {
            cat_html = cat_html + "<li>" + cat_res[rsb.cat][i].src + ": "
                                + cat_res[rsb.cat][i].score + "</li>";
        }
        $("ul#" + rsb.cat + "-match").html(cat_html);
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
*/
});
