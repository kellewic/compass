require.config({
    waitSeconds: 0,
    paths: {
        driver: '../app/compass/driver.min',
        mustache: '../app/compass/mustache.min'
    },
    shim: {
        'driver': {
            exports: 'Driver'
        },
        'mustache': {
            exports: 'Mustache'
        }
    }
});

require([
    "jquery",
    "underscore",
    "driver",
    "mustache",
    'splunkjs/mvc',
    "splunkjs/ready!",
    "splunkjs/mvc/simplexml/ready!"
],
function(
    $,
    _,
    Driver,
    Mustache,
    mvc
){
    var currentUrl = window.location.href;

    const pageHelpDriver = new Driver();

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
                    data = data.replace(/^b'\s*/, "");
                    data = data.replace(/'$/, "");
                    data = $.parseHTML($.trim(data), null);

                    dataHandler($('<div>').append(data));
                }
            });
        };

        var tmpl = '<span class="interests-panel-title">{{category}}</span><ul>{{#eles}}<li><a target="_blank" href="{{link}}">{{title}}</a> - {{body}}</li>{{/eles}}</ul>';

        // process Data Insider URL
        getUrlData("data_insider", function(div){
            // only keep this many results for display
            var max_results = 5;
            var map = new Map();
            var selector = div.find('a.carousel-card');
            var rendered_tmpl = "";

            selector.each(function(){
                var obj = $(this);

                var category = $.trim(obj.find('.splunk2-eyebrow').text()).toUpperCase();
                var title = $.trim(obj.find('.splunk2-h4').text());
                var body = $.trim(obj.find('.splunk-body p').text());

                var link = obj.attr('href');
                link = link.replace(/^https:\/\/www\.splunk\.com/, "");
                link = "https://www.splunk.com" + link;

                // merge these together to reduce number of dashboard panels
                if (category == "IT OPERATIONS"){
                    category = "IT";
                }

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

            $('div#insider_it_panel').append(Mustache.render(tmpl, {"category": "IT Operations", "eles": map.get("IT")}));
            $('div#insider_security_panel').append(Mustache.render(tmpl, {"category": "Security", "eles": map.get("SECURITY")}));
            $('div#insider_data_panel').append(Mustache.render(tmpl, {"category": "Data & Analytics", "eles": map.get("DATA & ANALYTICS")}));
            $('div#insider_tech_panel').append(Mustache.render(tmpl, {"category": "Emerging Technologies", "eles": map.get("EMERGING TECHNOLOGIES")}));
        });
    }
});




