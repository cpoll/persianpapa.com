(() => {
    function updateStats(){
        const TIMES_VISITED_KEY = 'timesVisited';
        const FIRST_VISIT_KEY = 'fistVisit';
        const LAST_VISIT_KEY = 'lastVisit';

        let timesVisited = Cookies.get(TIMES_VISITED_KEY);
        if(timesVisited) {
            timesVisited++;

            const statsElement = document.getElementsByClassName('stats')[0];

            const lastVisit = Cookies.get(FIRST_VISIT_KEY);
            formattedDate = new Date(lastVisit).toLocaleDateString("en-CA", {month: 'long', year: "numeric", day: "numeric"});

            statsElement.innerHTML = `Your browser has gone wandering ${timesVisited} times since ${formattedDate}`;
        }
        else {
            timesVisited = 1;
            Cookies.set(FIRST_VISIT_KEY, Date.now());
        }

        Cookies.set(LAST_VISIT_KEY, Date.now());
        Cookies.set(TIMES_VISITED_KEY, timesVisited);
    }

    document.addEventListener("DOMContentLoaded", updateStats);
})();