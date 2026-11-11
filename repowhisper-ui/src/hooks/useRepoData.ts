import {useState, useEffect} from 'react';
import type { RepoData } from '../types';

export function useRepoData() {
    const [data, setData] = useState<RepoData | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                const response = await fetch("./data.json");

                if (!response.ok) {
                    throw new Error(`HTTP error: ${response.status} - data.json file not found`);
                }

                const jsonData: RepoData = await response.json();
                setData(jsonData);
            } catch (err: any) {
                setError(err.message || "Unknown error during the loading");
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    return {data, loading, error};
}