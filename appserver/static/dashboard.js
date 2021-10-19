require.config({
    waitSeconds: 0,
    paths: {
        driver: '../app/compass/3rdparty/driver.min',
        mustache: '../app/compass/3rdparty/mustache.min'
    },
    shim: {
        'driver': { exports: 'Driver' },
        'mustache': { exports: 'Mustache' }
    }
});

require([
    "jquery",
    "underscore",
    "driver",
    "mustache",
    "splunkjs/ready!",
    "splunkjs/mvc/simplexml/ready!"
],
function(
    $,
    _,
    Driver,
    Mustache
){
    var currentUrl = window.location.href;
    const pageHelpDriver = new Driver();

    // Check to make sure we're running under a valid Splunk version. This affects showing
    // dynamic content since the underlying Python REST endpoint only supports Python 3.
    var splunkVersionIsValid = false;
    var splunkVersion = Splunk.util.getConfigValue("VERSION_LABEL", 0);
    try {
        if (+splunkVersion.replace(/\..*$/, "") >= 8) splunkVersionIsValid = true;
    }
    catch(e) {
        console.log("COMPASS ERROR: Can't determine Splunk version; disabling dynamic content");
    }

    if (currentUrl.endsWith('discover')) {
        // main page tour
        var pageHelpNode = $('<button id="page-help" class="btn btn-mini">Page Help</button>');

        pageHelpNode.on('click', (e) => {
            e.stopPropagation();

            if (pageHelpDriver.isActivated){
                pageHelpDriver.reset(true);
            }

            pageHelpDriver.start();
        });

        $('div.dashboard-header').prepend(pageHelpNode);

        pageHelpDriver.defineSteps([
            {
                element: '#page-help',
                popover: {
                    title: 'Compass',
                    description: 'Compass helps keep you oriented on your data maturity journey.',
                    position: 'bottom'
                }
            },
            {
                element: '#top_header',
                popover: {
                    title: 'Main Pillars',
                    description: 'Compass covers ITOps, Security, and DevOps across 6 common activities.',
                    position: 'bottom'
                }
            },
            {
                element: '#collect',
                popover: {
                    title: 'Collect',
                    description: 'This activity covers collecting data from any sources you deem important.',
                    position: 'bottom'
                }
            },
            {
                element: '#investigate',
                popover: {
                    title: 'Investigate',
                    description: 'This activity covers investigating the data you\'re now collecting to figure out what\'s important.',
                    position: 'bottom'
                }
            },
            {
                element: '#monitor',
                popover: {
                    title: 'Monitor',
                    description: 'This activity covers monitoring the data you\'ve investigated so you are alerted when known events happen.',
                    position: 'bottom'
                }
            },
            {
                element: '#triage',
                popover: {
                    title: 'Triage',
                    description: 'This activity covers triaging all the monitored events so you can deal with any issues.',
                    position: 'bottom'
                }
            },
            {
                element: '#analyze',
                popover: {
                    title: 'Analyze',
                    description: 'This activity covers analyzing and adapting to not only known, but unknown events via predictive analytics and machine learning.',
                    position: 'bottom'
                }
            },
            {
                element: '#automate',
                popover: {
                    title: 'Automate',
                    description: 'This activity covers automating your responses to changes in your data.',
                    position: 'bottom'
                }
            },
            {
                element: 'div.action-link',
                popover: {
                    title: 'Actions',
                    description: 'The action links related to each pillar and activity provide high-level information on how you might accomplish the action.',
                    position: 'bottom',
                    nextBtnText: 'Check it out'
                },
                onNext: () => {
                    pageHelpDriver.preventMove();

                    setTimeout(() => {
                        window.location.href = '/app/compass/itops__investigate__troubleshoot?run_tour=1';
                    }, 0);
                }
            },
            {
                element: 'div.action-link',
                popover: {
                    title: '',
                    description: ''
                }
            }
        ]);
    }
    // detail pages tour
    else if (currentUrl.match(/\/\w+__\w+__\w+\?run_tour=1/)){
        pageHelpDriver.defineSteps([
            {
                element: 'div.overview',
                popover: {
                    title: 'Overview',
                    description: 'The action detail pages start with a high-level overview.',
                    position: 'bottom'
                }
            },
            {
                element: 'div.platform',
                popover: {
                    title: 'Platform',
                    description: 'This area shows what Splunk products can help with this action.',
                    position: 'bottom'
                }
            },
            {
                element: 'div.related',
                popover: {
                    title: 'Related Actions',
                    description: 'A list of related actions helps you navigate to similar items.',
                    position: 'bottom'
                }
            },
            {
                element: 'div.basics',
                popover: {
                    title: 'The Basics',
                    description: 'This area gives you high-level guidance on how to start implementing this action.',
                    position: 'bottom'
                }
            },
            {
                element: 'div.help',
                popover: {
                    title: 'Help and Guidance',
                    description: 'This area provides links to additional information to help you with this action.',
                    position: 'bottom',
                    nextBtnText: 'Back to Discover'
                },
                onNext: () => {
                    pageHelpDriver.preventMove();

                    setTimeout(() => {
                        window.location.href = '/app/compass/discover';
                    }, 0);
                }
            },
            {
                element: 'div.basics',
                popover: {
                    title: '',
                    description: ''
                }
            }
        ]);

        if (pageHelpDriver.isActivated){
            pageHelpDriver.reset(true);
        }

        pageHelpDriver.start();
    }
    else if (currentUrl.endsWith('stay_current')) {
        // Check for good Splunk version
        if (splunkVersionIsValid === false){
            // Hide normal dashboard content
            $("div#row1").css('display', 'none');
            $("div#row2").css('display', 'none');
            $('div[id*="interests_"').css('display', 'none');

            // Display version warning
            $("div#version_warning").css('display', 'block');
            return;
        }


        // get URL data via CORS proxy
        var getUrlData = function(urlName, dataHandler){
            var loc = window.location;
            var url_prefix = loc.origin + loc.pathname.replace(/\/app\/.*$/, "");
            var rest_endpoint = url_prefix + "/splunkd/__raw/services/compass/v1/cors_proxy/" + urlName;

            $.ajax({
                url: rest_endpoint,
                type: "GET",
                dataType: "text",
                success: function(data){
                    data = data.trim();

                    if (data.startsWith("Warn: ")) {
                        data = '<span class="url-error">' + data + '</span>';
                    }
                    else {
                        data = $.parseHTML(data, null);
                    }

                    dataHandler($('<div>').append(data));
                }
            });
        };

        // HTML template for panel content
        var tmpl = '{{#category}}<span class="interests-panel-title">{{category}}</span>{{/category}}';
        tmpl = tmpl + '{{#eles}}<ul><li><a target="_blank" href="{{link}}">{{title}}</a> - {{body}}</li></ul>{{/eles}}';

        // only keep this many results for display
        var max_results = 5;

        // process Data Insider URL
        getUrlData("data_insider", function(div){
            var error = div.find('span.url-error');

            if (error.length > 0) {
                $('div#insider_left_panel').append(error);
                return;
            }

            // bring in data as JSON object
            var selector = JSON.parse(div.text().trim()).dataInsiderList;

            // translate date string to epoch time
            for (let i = 0; i < selector.length; i++) {
                selector[i]["createdDate"] = new Date(selector[i]["createdDate"]).getTime();
            }

            // sort data by epoch time descending
            selector = selector.sort((a, b) => b.createdDate - a.createdDate);

            // create container to store data to display
            var map = new Map().set("LEFT", []).set("RIGHT", []);
            var item, cat, category;

            for (let i = 0; i < selector.length; i++) {
                item = selector[i];
                category = (i % 2 == 0) ? "LEFT" : "RIGHT";

                cat = map.get(category);

                if (cat.length < max_results){
                    cat.push({
                        "link": "https://www.splunk.com" + item["ctaLink"].replace(/^https:\/\/www\.splunk\.com/, ""),
                        "title": item["headlineText"].trim(),
                        "body": item["bodyText"].trim().replace(/(?:\\u[0-9a-fA-F]{1,4}|<)\/?p(?:\\u[0-9a-fA-F]{1,4}|>)/g, "")
                    });
                }
            }

            $('div#insider_left_panel').append(Mustache.render(tmpl, {"eles": map.get("LEFT")}));
            $('div#insider_right_panel').append(Mustache.render(tmpl, {"eles": map.get("RIGHT")}));
        });

        // Wrapper function for Splunk Blog article parsing
        var getBlogData = function(urlName, panelName, panelTitle){
            getUrlData(urlName, function(div){
                var error = div.find('span.url-error');

                if (error.length > 0) {
                    return;
                }

                var selector = div.find('section#mosaic-tiles div.tile-content');
                var rendered_tmpl = "";
                var map = new Map();
                var category;

                selector.each(function(){
                    var obj = $(this);

                    category = $.trim(obj.find('span.category-name').text()).toUpperCase();
                    var title = $.trim(obj.find('div.text-section .tile-heading').text());
                    var body = $.trim(obj.find('p.tile-desc').text());

                    var link = obj.find('div.tile-link a').attr('href');
                    link = link.replace(/^https:\/\/www\.splunk\.com/, "");
                    link = "https://www.splunk.com" + link;

                    var card_data = {
                        "category": category,
                        "link": link,
                        "title": title,
                        "body": body,
                    };

                    if (map.has(category)){
                        var cat = map.get(category);
                        if (cat.length < max_results){
                            cat.push(card_data);
                        }
                    }
                    else {
                        map.set(category, [card_data]);
                    }
                });

                $('div#' + panelName).append(Mustache.render(tmpl, {"category": panelTitle, "eles": map.get(category)}));
            });
        };

        getBlogData("blog_devops", "blog_devops_panel", "DevOps");
        getBlogData("blog_it", "blog_it_panel", "IT");
        getBlogData("blog_security", "blog_security_panel", "Security");
        getBlogData("blog_platform", "blog_platform_panel", "Platform");
        getBlogData("blog_tips_and_tricks", "blog_tips_and_tricks_panel", "Tips & Tricks");
        getBlogData("blog_events", "blog_events_panel", "Events");
    }
});

