$(document).ready(function() {

    // extract parameters for sources and wa_key:
    // NOTE: need to also provide prios so we can sequence
    // submissions accordingly (or pre-sort params within cat)
    var pmap = {
        wa_key: $("param#wa-key").attr("value"),
        search_str: $("param#search-str").attr("value"),
        match_score: parseFloat($("param#match-score").attr("value")),
        min_wc: parseInt($("param#min-wc").attr("value"), 10),
        back_days: parseInt($("param#back-days").attr("value"), 10)
    };
    var cat_src = {};
    var params = $("param.cat-src");
    for (var i = 0; i < params.length; i++) {
        var cat = params.eq(i).attr("name");
        var src_str = params.eq(i).attr("value");
        if (src_str.length > 0) {
            cat_src[cat] = src_str.split(' ');
        }
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
                'status': 0,    //  1: submitted, got job_id
                                //  2: have result
                                //  3: published
                                // -1: failed
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
            timeout: 5000,
            eror: function(xhr, status, errorThrown) {
                score_board[xhr.responseJSON.src].status = -1;
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
                        switch (json.status) {
                            case 'finished' :
                                score_board[json.src].status = 2;
                                score_board[json.src].result = json.result;
                                break;
                            case 'failed':
                                score_board[json.src].status = -1;
                                score_board[json.src].result = [];
                                break;
                            default:
                                var timeout = fetch_timeout +
                                              2000 * (1 - score_board_fill);
                                setTimeout(pollForID(src), timeout);
                        }
                    },
                    timeout: 5000,
                    eror: function(xhr, status, errorThrown) {
                        score_board[xhr.responseJSON.src].status = -1;
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

    // setup results by category:
    var cat_res = {};
    for (var cat in cat_src) {
        cat_res[cat] = [];
    }

    function compare_score(a, b) {
        // a and b will be elements of one of cat_res' result lists
        return b.score- a.score;
    }

    function render_cat_result(cres, min_match, min_wc) {
        // renders results for a specific category and returns html
        var num_items = cres.length;
        var ht = "";
        for (var i = 0; i < num_items; i++) {
            if (cres[i].score < min_match || cres[i].wc < min_wc) {
                continue;
            }
            ht = ht + '<h3><a href="' + cres[i]['url'] + '">' + cres[i]['title'] + '</a></h2>'
                    + '<h4>' + cres[i]['link'] + '</h3>'
                    + '<p class="match-score">' + cres[i]['wc'] + ' words, score: ' + cres[i]['score'].toFixed(2) + '</p>'
                    + '<p class="res-description">' + cres[i]['desc'] + '</p>';
        }
        return ht;
    }

    function insert_result(res_src, min_match, min_wc) {
        var rsb = score_board[res_src];
        if (rsb.result.length == 0) {
            return;
        }
        cat_res[rsb.cat] = cat_res[rsb.cat].concat(rsb.result);
        cat_res[rsb.cat].sort(compare_score);
        //now update HTML:
        var old_ht = $("div#" + rsb.cat + "-match").html();
        var new_ht = render_cat_result(cat_res[rsb.cat], min_match,
                                       min_wc);
        if (new_ht.length > old_ht.length) {
            $("div#" + rsb.cat + "-match").fadeOut("fast");
            $("div#" + rsb.cat + "-match").html(new_ht);
            $("div#" + rsb.cat + "-match").fadeIn("fast");
        }
    }

    $("#progress-text").html("<p>Searching " + score_board_size
            + " sources ...</p>");
    $("#progress-bar").progressbar({value: 1});
    $("#progress-text").fadeIn("slow");
    $("#progress-bar").fadeIn("slow");

    // check score board:
    function keep_score() {
        for (var src in score_board) {
            if (score_board[src].status == 2) {
                if (fin_count == 0) {
                    $(".spectrum").fadeIn("slow");
                }
                ++fin_count;
                insert_result(src, pmap.match_score/100, pmap.min_wc);
                score_board[src].status = 3;
            }
            if (score_board[src].status == -1) {
                ++fail_count;
                score_board[src].status == -2;
            }
        }
        score_board_fill = (fin_count + fail_count) / score_board_size;
        if (score_board_fill > 0.0001) {
            $("#progress-text").html("<p>Searched "
                    + (fin_count + fail_count) + " of "
                    + score_board_size + " sources</p>");
            $("#progress-bar").progressbar({value: score_board_fill * 100});
        };
        if ((fin_count + fail_count) < score_board_size) {
            var timeout = 500 + 2000 * (1 - score_board_fill);
            console.log("fin_count: " + fin_count);
            setTimeout(keep_score, timeout);
        }
        else {
            // switch off progress bar
            setTimeout(function() {
                $("#progress-box").slideUp("fast");
                $("#results-top-box").fadeIn("fast");}, 750);
            console.dir(score_board);
        }
    }
    var fin_count = 0;
    var fail_count = 0;
    setTimeout(keep_score, 3000);
});
