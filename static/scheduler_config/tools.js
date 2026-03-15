

    console.log(data)

    const renderFleetJobs = () => {

        const style = document.createElement('style');
        style.textContent = `
            .text-neon-green { color: #39FF14 !important; text-shadow: 0 0 5px rgba(57, 255, 20, 0.4); }
            .text-neon-blue { color: #00D4FF !important; text-shadow: 0 0 5px rgba(0, 212, 255, 0.4); }
        `;
        document.head.appendChild(style);

        const container = document.getElementById('scheduled-jobs');
        container.innerHTML = '';

        // --- FIXED HEADER ROW ---
        const headerRow = document.createElement('div');
        headerRow.className = 'row mb-2 border-bottom pb-3 fw-bold text-primary small align-items-center';

        // 1. Host Header (Matches col-md-2)
        const hostHead = document.createElement('div');
        hostHead.className = 'col-md-2';
        hostHead.textContent = 'HOST';
        headerRow.appendChild(hostHead);

        // 2. Jobs Header Group (Matches col-md-10)
        const jobsHeadCol = document.createElement('div');
        jobsHeadCol.className = 'col-md-10 d-flex';

        ['JOB ID', 'TRIGGER', 'LAST RUN','NEXT RUN'].forEach(txt => {
            const div = document.createElement('div');
            div.className = 'col-3'; // Matches the col-4 inside the loop
            div.textContent = txt;
            jobsHeadCol.appendChild(div);
        });

        headerRow.appendChild(jobsHeadCol);
        container.appendChild(headerRow);
        // --- END FIXED HEADER ROW ---

        Object.entries(data).forEach(([hostname, host_info]) => {
            const jobs = host_info.jobs;

            // 1. Create a wrapper for the Host Row
            const hostRow = document.createElement('div');
            hostRow.className = 'row mb-4 border-bottom pb-3';

            const leader_role = host_info.leader_role;
            const leader_state = host_info.leader_state;

            let state_class = "text-secondary"
            if ( leader_state === "STANDBY" )
            {
                state_class = "text-neon-blue";
            } else if ( leader_state === "ACTIVE" )
            {
                state_class = "text-neon-green";            }

            let role_text = ""
            let role_class = ""
            if ( leader_role == "FOLLOWER" ) {
                role_class = ""
                role_text = " (follower)"
            } else if ( leader_role == "LEADER" ) {
                role_class = "fw-bold"
                role_text = " (leader)"
            }

            // 2. Create the Host Title Column (Column 1)
            const hostTitle = document.createElement('div');
            hostTitle.className = 'col-md-2 ' + ' ' + role_class + ' ' + state_class + ' pt-2';

            hostTitle.textContent = hostname + role_text;
            hostRow.appendChild(hostTitle);

            // 3. Create the Jobs Column (Column 2)
            const jobsCol = document.createElement('div');
            jobsCol.className = 'col-md-10';

            const jobUl = document.createElement('ul');
            jobUl.className = 'list-group list-group-flush w-100';

            if (Array.isArray(jobs) && jobs.length > 0) {
                jobs.forEach(job => {
                    const jobLi = document.createElement('li');
                    jobLi.className = 'list-group-item d-flex align-items-center border-0 small';

                    const jobData = [job.id, job.trigger, new Date(job.last_run).toLocaleString(), new Date(job.next_run).toLocaleString() ];
                    jobData.forEach(text => {
                        const cell = document.createElement('div');
                        cell.className = 'col-3 text-truncate';

                        cell.textContent = text;
                        jobLi.appendChild(cell);
                    });
                    jobUl.appendChild(jobLi);
                });
            } else {
                const emptyLi = document.createElement('li');
                emptyLi.className = 'list-group-item text-muted font-italic border-0 small';
                emptyLi.textContent = 'No active jobs reported.';
                jobUl.appendChild(emptyLi);
            }

            jobsCol.appendChild(jobUl);
            hostRow.appendChild(jobsCol);
            container.appendChild(hostRow);
        });
    };

    renderFleetJobs();