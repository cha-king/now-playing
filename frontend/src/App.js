import RecentlyPlayed from './RecentlyPlayed';
import NowPlaying from './NowPlaying';
import styles from './App.module.css';

function App() {
  return (
    <div className={styles.app}>
      <NowPlaying/>
      {/* <RecentlyPlayed/> */}
    </div>
  )
}

export default App;
