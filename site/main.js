(() => {

    function visitMeetsThreshhold(lastVisit) {
        const THRESHHOLD_SECONDS = 60 * 5;

        if(!lastVisit) {
            return False;
        }

        return Date.now() - parseInt(lastVisit) > 1000 * THRESHHOLD_SECONDS;
    }

    function updateStats(){
        const TIMES_VISITED_KEY = 'timesVisited';
        const FIRST_VISIT_KEY = 'firstVisit';
        const LATEST_VISIT_KEY = 'lastVisit';

        let timesVisited = Cookies.get(TIMES_VISITED_KEY);
        const firstVisit = Cookies.get(FIRST_VISIT_KEY);
        const latestVisit = Cookies.get(LATEST_VISIT_KEY);

        if(timesVisited && firstVisit) {
            if(visitMeetsThreshhold(latestVisit)) {
                Cookies.set(TIMES_VISITED_KEY, ++timesVisited);
                Cookies.set(LATEST_VISIT_KEY, Date.now());
            }

            const statsElement = document.getElementsByClassName('stats')[0];

            formattedDate = new Date(parseInt(firstVisit)).toLocaleDateString("en-CA", {month: 'long', year: "numeric", day: "numeric"});

            statsElement.innerHTML = `Your browser has gone wandering ${timesVisited} times since ${formattedDate}`;
        }
        else {
            Cookies.set(TIMES_VISITED_KEY, 1);
            Cookies.set(FIRST_VISIT_KEY, Date.now());
            Cookies.set(LATEST_VISIT_KEY, Date.now());
        }
    }

    document.addEventListener("DOMContentLoaded", updateStats);
})();