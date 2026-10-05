// Package jobs runs thumbnail jobs and collects their results.
package jobs

import "sync"

// Job is one image to thumbnail.
type Job struct {
	ID   string
	Path string
}

// Result is the outcome of processing one Job.
type Result struct {
	ID    string
	Bytes int
	Err   error
}

// RunAll processes every job concurrently and returns the results keyed by job ID.
func RunAll(jobs []Job, process func(Job) Result) map[string]Result {
	results := make(map[string]Result, len(jobs))
	var wg sync.WaitGroup
	for _, j := range jobs {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results[j.ID] = process(j)
		}()
	}
	wg.Wait()
	return results
}
