async function fetchEvents() {
    const response = await fetch('/events');
    const data = await response.json();
    const list = document.getElementById('events-list');
    list.innerHTML = '';

    data.forEach(event => {
        const li = document.createElement('li');
        const istTime = formatIST(event.timestamp);

        let msg = '';
        if (event.type === 'push') {
            msg = `${event.author} pushed to ${event.to_branch} on ${istTime}`;
        } else if (event.type === 'pull_request') {
            msg = `${event.author} submitted a pull request from ${event.from_branch} to ${event.to_branch} on ${istTime}`;
        } else if (event.type === 'merge') {
            msg = `${event.author} merged branch ${event.from_branch} to ${event.to_branch} on ${istTime}`;
        }

        li.textContent = msg;
        list.appendChild(li);
    });
}

// Converts ISO timestamp to IST time string
function formatIST(timestamp) {
    const utcDate = new Date(timestamp);
    const IST_OFFSET = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30
    const istDate = new Date(utcDate.getTime() + IST_OFFSET);

    return istDate.toLocaleString("en-IN", {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    }) + " IST";
}

fetchEvents();
setInterval(fetchEvents, 15000);