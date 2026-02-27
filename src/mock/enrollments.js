export const MOCK_ENROLLMENTS = [
  { id: 'e001', trainingId: 't001', userId: 'u003', name: '张伟', policeId: 'GX-NN-2056', unit: '南宁市青秀区刑警大队', phone: '136****0003', enrollTime: '2025-02-18 09:23', status: 'approved', note: '' },
  { id: 'e002', trainingId: 't001', userId: 'u004', name: '陈小明', policeId: 'GX-NN-2101', unit: '南宁市江南区派出所', phone: '158****1122', enrollTime: '2025-02-18 10:45', status: 'approved', note: '' },
  { id: 'e003', trainingId: 't001', userId: 'u005', name: '刘芳', policeId: 'GX-NN-2234', unit: '南宁市西乡塘交警大队', phone: '135****3344', enrollTime: '2025-02-19 08:30', status: 'pending', note: '' },
  { id: 'e004', trainingId: 't001', userId: 'u006', name: '黄志远', policeId: 'GX-GL-1045', unit: '桂林市秀峰区派出所', phone: '139****5566', enrollTime: '2025-02-19 14:20', status: 'pending', note: '' },
  { id: 'e005', trainingId: 't001', userId: 'u007', name: '梁美华', policeId: 'GX-ZZ-0892', unit: '柳州市城中区刑警队', phone: '186****7788', enrollTime: '2025-02-20 09:15', status: 'rejected', note: '名额已满，下期优先录取' },
  { id: 'e006', trainingId: 't001', userId: 'u008', name: '覃建军', policeId: 'GX-GL-2156', unit: '桂林市灵川县公安局', phone: '182****9900', enrollTime: '2025-02-20 11:30', status: 'approved', note: '' },
  { id: 'e007', trainingId: 't002', userId: 'u003', name: '张伟', policeId: 'GX-NN-2056', unit: '南宁市青秀区刑警大队', phone: '136****0003', enrollTime: '2025-03-01 08:00', status: 'approved', note: '' },
  { id: 'e008', trainingId: 't002', userId: 'u009', name: '韦国强', policeId: 'GX-BS-0334', unit: '百色市右江区派出所', phone: '173****1234', enrollTime: '2025-03-01 10:22', status: 'pending', note: '' },
]

// 培训班名额信息
export const TRAINING_QUOTA = {
  t001: { total: 50, approved: 32, pending: 8 },
  t002: { total: 40, approved: 20, pending: 5 },
  t003: { total: 30, approved: 28, pending: 2 },
}
