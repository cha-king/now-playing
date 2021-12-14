import { useState, useEffect } from 'react';

import styles from './NowPlaying.module.css';

function NowPlaying() {
    const [song, setSong] = useState(null);
    
    useEffect(() => {
        async function getNowPlaying() {
            const response = await fetch('/api/now-playing');
            if (response.status === 204) {
                setSong(null);
            }
            const data = await response.json();
            setSong(data);
        }
        getNowPlaying();
    }, []);

    useEffect(() => {
        function connect() {
            // TODO: Find workaround for CRA proxy not working for WS on Chrome
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
            const url = `${protocol}//${window.location.host}/api/ws/now-playing`;
            // const url = 'ws://localhost:8000/api/ws/now-playing';
            const ws = new WebSocket(url);
            ws.onmessage = function(event) {
                const song = JSON.parse(event.data);
                setSong(Object.keys(song).length !== 0 ? song : null);
            };
            ws.onclose = function(event) {
                const delay = 1000 + Math.random() * 1000;
                setTimeout(connect, delay)
            };
        }
        connect();
    }, []);

    if (song === null) {
        return (
            <div className={styles.empty}>
                <div>
                    <p>Nothing is currently playing..</p>
                    <p>Check back later!</p>
                </div>
            </div>
        )
    }
    
    // return (<Song title={song.name} artist={song.artist} album={song.album} imageUrl={song.image_url}/>)
    return (
        <div className={styles['now-playing']}>
            <img src={song.image_href} alt={song.album}/>
            <ul>
                <li className={styles['song-name']}>
                    <a href={song.song_href} target="_blank" rel="noreferrer">
                        {song.name}
                    </a>
                </li>
                <li className={styles['album-name']}>
                    <a href={song.album_href} target="_blank" rel="noreferrer">
                        {song.album}
                    </a>
                </li>
                <li className={styles['artist-name']}>
                    <a href={song.artist_href} target="_blank" rel="noreferrer">
                        {song.artist}
                    </a>
                </li>
            </ul>
        </div>
    )
}

export default NowPlaying;
